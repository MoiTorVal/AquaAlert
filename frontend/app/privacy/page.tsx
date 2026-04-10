import Link from "next/link";

export const metadata = {
  title: "Privacy Policy | WaterStress",
  description:
    "WaterStress privacy policy — how we collect, use, and protect your data",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-bg-primary pt-32 pb-24 px-8">
      <div className="max-w-3xl mx-auto">
        <Link
          href="/"
          className="text-muted hover:text-white text-sm font-medium"
        >
          &larr; Back to home
        </Link>

        <h1 className="text-4xl font-bold text-surface mt-8 mb-2">
          Privacy Policy
        </h1>
        <p className="text-muted text-sm mb-12">
          Effective date: April 9, 2026
        </p>

        <div className="prose prose-invert prose-sm max-w-none text-white/70 space-y-8">
          <p>
            At WaterStress (&quot;WaterStress,&quot; &quot;we,&quot;
            &quot;us,&quot; or &quot;our&quot;), we take your privacy seriously.
            Please read this Privacy Policy to learn how we treat your personal
            data. By using or accessing our water stress monitoring Services in
            any manner, you acknowledge that you accept the practices and
            policies outlined below, and you hereby consent that we will
            collect, use, and share your information as described in this
            Privacy Policy.
          </p>
          <p>
            Remember that your use of WaterStress&apos;s Services is at all
            times subject to our{" "}
            <Link
              href="/terms"
              className="text-muted hover:text-white underline"
            >
              Terms of Service
            </Link>
            . Any terms we use in this Policy without defining them have the
            definitions given to them in the Terms of Service.
          </p>
          <p>
            If you have a disability, you may access this Privacy Policy in an
            alternative format by contacting support@waterstress.io.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            What this Privacy Policy Covers
          </h2>
          <p>
            This Privacy Policy covers how we treat Personal Data that we gather
            when you access or use our Services, including the WaterStress web
            application, mobile application, API integrations, and any connected
            field sensors or weather station interfaces. &quot;Personal
            Data&quot; means any information that identifies or relates to a
            particular individual and also includes information referred to as
            &quot;personally identifiable information&quot; or &quot;personal
            information&quot; under applicable data privacy laws, rules, or
            regulations. This Privacy Policy does not cover the practices of
            companies we don&apos;t own or control or people we don&apos;t
            manage.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Personal Data
          </h2>
          <h3 className="text-lg font-medium text-surface">
            Categories of Personal Data We Collect
          </h3>
          <h4 className="text-base font-medium text-surface ">
            Profile or Contact Data
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>First and last name</li>
            <li>Email address</li>
            <li>Phone number</li>
            <li>Physical address or farm/ranch mailing address</li>
            <li>Unique identifiers such as account passwords</li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers; Parties You Authorize, Access, or
            Authenticate.
          </p>
          <h4 className="text-base font-medium text-surface">Payment Data</h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Payment card type</li>
            <li>Last 4 digits of payment card</li>
            <li>Billing address, phone number, and email</li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers (specifically our payment processing
            partner, Stripe).
          </p>
          <h4 className="text-base font-medium text-surface">Device/IP Data</h4>
          <ul className="list-disc list-inside space-y-1">
            <li>IP address</li>
            <li>Device ID</li>
            <li>
              Type of device, operating system, and browser used to access the
              Services
            </li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers; Parties You Authorize, Access, or
            Authenticate.
          </p>
          <h4 className="text-base font-medium text-surface">Web Analytics</h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Web page interactions</li>
            <li>
              Referring webpage or source through which you accessed the
              Services
            </li>
            <li>
              Statistics associated with interactions between your device and
              the Services
            </li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers; Parties You Authorize, Access, or
            Authenticate.
          </p>
          <h4 className="text-base font-medium text-surface">
            Field and Sensor Data
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>GPS coordinates or parcel boundaries of monitored fields</li>
            <li>
              Crop type, planting date, and growth stage information you provide
            </li>
            <li>
              Soil type, root zone depth, and irrigation system configuration
            </li>
            <li>
              Sensor telemetry including soil moisture readings, if applicable
            </li>
            <li>
              Reference evapotranspiration (ET&#x2080;) data retrieved from
              public weather station networks (e.g., CIMIS)
            </li>
            <li>
              Calculated water balance outputs including crop
              evapotranspiration, soil moisture depletion, and stress forecasts
            </li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers; Groundwater Sustainability Agencies
            (only if you opt in to SGMA compliance reporting).
          </p>
          <h4 className="text-base font-medium text-surface">
            Other Identifying Information that You Voluntarily Choose to Provide
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>
              Identifying information in emails, support tickets, or feedback
              you send us
            </li>
          </ul>
          <p className="text-xs text-muted">
            Shared with: Service Providers; Business Partners; Parties You
            Authorize, Access, or Authenticate.
          </p>
          <h3 className="text-lg font-medium text-surface">
            Categories of Sources of Personal Data
          </h3>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>You:</strong> When you provide information directly to us,
              create an account, configure field or crop profiles, use our
              interactive tools and Services, respond to surveys, send us an
              email, or otherwise contact us.
            </li>
            <li>
              <strong>Automatic Collection:</strong> Through cookies, server
              logs, and application telemetry when you use the Services. If you
              use a location-enabled browser or our mobile application, we may
              receive information about your location.
            </li>
            <li>
              <strong>Public Data Sources:</strong> We retrieve publicly
              available weather and evapotranspiration data from government
              agencies and public weather station networks such as CIMIS.
            </li>
            <li>
              <strong>Third Parties:</strong> We may use analytics providers to
              analyze how you interact with the Services, or third parties may
              help us provide you with customer support.
            </li>
          </ul>
          <h3 className="text-lg font-medium text-surface">
            Our Commercial or Business Purposes for Collecting Personal Data
          </h3>
          <h4 className="text-base font-medium text-surface">
            Providing, Customizing, and Improving the Services
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Creating and managing your account or user profiles</li>
            <li>Processing orders or other transactions; billing</li>
            <li>
              Computing FAO-56 soil water balance calculations and generating
              irrigation scheduling recommendations
            </li>
            <li>
              Delivering water stress forecasts and alerts to your configured
              notification channels
            </li>
            <li>
              Generating SGMA compliance reports on your behalf, if you opt in
            </li>
            <li>
              Improving the Services, including testing, research, internal
              analytics, and product development
            </li>
            <li>
              Personalizing the Services based on your crop types, field
              configurations, and preferences
            </li>
            <li>Fraud protection, security, and debugging</li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Marketing the Services
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Marketing and selling the Services</li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Corresponding with You
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Responding to correspondence that we receive from you</li>
            <li>
              Sending you emails, alerts, and other communications according to
              your preferences
            </li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Meeting Legal Requirements and Enforcing Legal Terms
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>
              Fulfilling our legal obligations under applicable law, regulation,
              court order, or other legal process
            </li>
            <li>
              Protecting the rights, property, or safety of you, WaterStress, or
              another party
            </li>
            <li>Enforcing any agreements with you</li>
            <li>Resolving disputes</li>
          </ul>
          <p>
            We will not collect additional categories of Personal Data or use
            the Personal Data we collected for materially different, unrelated,
            or incompatible purposes without providing you notice.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            How We Share Your Personal Data
          </h2>
          <p>
            We disclose your Personal Data to the categories of service
            providers and other parties listed in this section. Depending on
            state laws that may be applicable to you, some of these disclosures
            may constitute a &quot;sale&quot; of your Personal Data. For more
            information, please refer to the state-specific sections below.
          </p>{" "}
          <h4 className="text-base font-medium text-surface">
            Service Providers
          </h4>{" "}
          <ul className="list-disc list-inside space-y-1">
            <li>Hosting, technology, and communication providers</li>
            <li>Cloud infrastructure providers (e.g., AWS)</li>
            <li>Security and fraud prevention consultants</li>
            <li>Analytics providers</li>
            <li>Support and customer service vendors</li>
            <li>
              Payment processors (please see Stripe&apos;s terms of service and
              privacy policy for information on its use and storage of your
              Personal Data)
            </li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Business Partners
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Agricultural technology partners and integration providers</li>
            <li>
              Companies that we partner with to offer joint promotional offers
              or opportunities
            </li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Groundwater Sustainability Agencies
          </h4>
          <p>
            If you voluntarily opt in to SGMA compliance reporting features, we
            may share field-level water use summaries with the applicable
            Groundwater Sustainability Agency in your basin. We will not share
            this data without your explicit consent.
          </p>
          <h4 className="text-base font-medium text-surface">
            Parties You Authorize, Access, or Authenticate
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>Third-party services you access through the Services</li>
            <li>Other users within your organization, if applicable</li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Legal Obligations
          </h4>
          <p>
            We may share any Personal Data that we collect with third parties in
            conjunction with any of the activities set forth under &quot;Meeting
            Legal Requirements and Enforcing Legal Terms&quot; above.
          </p>
          <h4 className="text-base font-medium text-surface">
            Business Transfers
          </h4>
          <p>
            All of your Personal Data that we collect may be transferred to a
            third party if we undergo a merger, acquisition, bankruptcy, or
            other transaction in which that third party assumes control of our
            business (in whole or in part). Should one of these events occur, we
            will make reasonable efforts to notify you before your information
            becomes subject to different privacy and security policies and
            practices.
          </p>
          <h4 className="text-base font-medium text-surface">
            Data that is Not Personal Data
          </h4>
          <p>
            We may create aggregated, de-identified, or anonymized data from the
            Personal Data we collect, including by removing information that
            makes the data personally identifiable to a particular user. We may
            use such data and share it with third parties for our lawful
            business purposes, provided that we will not share such data in a
            manner that could identify you.
          </p>{" "}
          <h2 className="text-xl font-semibold text-surface pt-4">
            Sensor and Field Data
          </h2>
          <p>
            WaterStress collects and processes field-level agricultural data to
            deliver its core irrigation scheduling and water stress monitoring
            Services.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Ownership.</strong> You retain full ownership of the field
              data, crop configuration, and sensor readings you provide or that
              are collected on your behalf. WaterStress does not claim ownership
              of your agricultural data.
            </li>
            <li>
              <strong>Use.</strong> We use your field and sensor data solely to
              provide, maintain, and improve the Services—including computing
              water balance models, generating irrigation recommendations, and
              producing stress forecasts. We may also use anonymized and
              aggregated field data to improve model accuracy across the
              platform.
            </li>
            <li>
              <strong>Sharing.</strong> We do not sell your field-level data to
              third parties. We share identifiable field data only with service
              providers who need it to operate the Services on our behalf, and
              with Groundwater Sustainability Agencies only if you explicitly
              opt in to SGMA reporting.
            </li>
            <li>
              <strong>Public Weather Data.</strong> The Services retrieve
              reference evapotranspiration and weather data from publicly
              available sources such as CIMIS. This data is not Personal Data
              and is used in calculations on your behalf.
            </li>
          </ul>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Tracking Tools and Opt-Out
          </h2>
          <p>
            The Services use cookies and similar technologies such as pixel
            tags, web beacons, clear GIFs, and JavaScript (collectively,
            &quot;Cookies&quot;) to enable our servers to recognize your web
            browser, tell us how and when you visit and use our Services,
            analyze trends, learn about our user base, and operate and improve
            our Services. Please note that because of our use of Cookies, the
            Services do not support &quot;Do Not Track&quot; requests sent from
            a browser at this time.
          </p>
          <p>We use the following types of Cookies:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Essential Cookies.</strong> Required for providing you
              with features or services that you have requested. Disabling these
              Cookies may make certain features and services unavailable.
            </li>
            <li>
              <strong>Functional Cookies.</strong> Used to record your choices
              and settings regarding our Services, maintain your preferences
              over time, and recognize you when you return.
            </li>
            <li>
              <strong>Performance/Analytical Cookies.</strong> Allow us to
              understand how visitors use our Services by collecting information
              about the number of visitors, what pages visitors view, and how
              long visitors are viewing pages.
            </li>
          </ul>
          <p>
            You can decide whether or not to accept Cookies through your
            internet browser&apos;s settings. If you disable Cookies, you may
            have to manually adjust some preferences every time you visit our
            website and some functionalities may not work.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Data Security and Retention
          </h2>
          <p>
            We seek to protect your Personal Data from unauthorized access, use,
            and disclosure using appropriate physical, technical,
            organizational, and administrative security measures. These measures
            include encryption of data in transit and at rest, role-based access
            controls, and regular security assessments. Although we work to
            protect the security of your account, please be aware that no method
            of transmitting data over the internet or storing data is completely
            secure.
          </p>
          <p>
            We retain Personal Data about you for as long as you have an open
            account with us or as otherwise necessary to provide you with our
            Services. Field and sensor data associated with your account is
            retained for the duration of your account and for up to 12 months
            following account closure, after which it is permanently deleted or
            anonymized.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Personal Data of Children
          </h2>
          <p>
            We do not knowingly collect or solicit Personal Information from
            anyone under the age of 13. If you are under 13, please do not
            attempt to register for the Services or send any Personal
            Information about yourself to us. If we learn that we have collected
            Personal Information from a child under age 13, we will delete that
            information as quickly as possible. If you believe that a child
            under 13 may have provided us Personal Information, please contact
            us at support@waterstress.io.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            State Law Privacy Rights
          </h2>
          <h3 className="text-lg font-medium text-surface">
            California Resident Rights
          </h3>
          <p>
            Under California Civil Code Sections 1798.83–1798.84, California
            residents are entitled to contact us to prevent disclosure of
            Personal Data to third parties for such third parties&apos; direct
            marketing purposes; in order to submit such a request, please
            contact us at support@waterstress.io.
          </p>
          <h3 className="text-lg font-medium text-surface">
            Nevada Resident Rights
          </h3>
          <p>
            If you are a resident of Nevada, you have the right to opt-out of
            the sale of certain Personal Data to third parties. You can exercise
            this right by contacting us at support@waterstress.io with the
            subject line &quot;Nevada Do Not Sell Request&quot; and providing us
            with your name and the email address associated with your account.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            European Union Data Subject Rights
          </h2>
          <h3 className="text-lg font-medium text-surface">EU Residents</h3>
          <p>
            If you are a resident of the European Union (&quot;EU&quot;), United
            Kingdom, Lichtenstein, Norway, or Iceland, you may have additional
            rights under the EU General Data Protection Regulation (the
            &quot;GDPR&quot;) with respect to your Personal Data. WaterStress
            will be the controller of your Personal Data processed in connection
            with the Services.
          </p>
          <h4 className="text-base font-medium text-surface">
            Processing Grounds
          </h4>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Contractual Necessity:</strong> We process Profile or
              Contact Data, Payment Data, Device Data, Web Analytics, and Field
              and Sensor Data as necessary to perform under our Terms of Service
              and provide you the Services.
            </li>
            <li>
              <strong>Legitimate Interest:</strong> We process certain Personal
              Data when we believe it furthers the legitimate interest of us or
              third parties, including providing and improving the Services,
              marketing, corresponding with you, and meeting legal requirements.
            </li>
            <li>
              <strong>Consent:</strong> In some cases, we process Personal Data
              based on the consent you expressly grant to us at the time we
              collect such data.
            </li>
            <li>
              <strong>Other Processing Grounds:</strong> From time to time we
              may also need to process Personal Data to comply with a legal
              obligation or to protect the vital interests of you or other data
              subjects.
            </li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            EU Data Subject Rights
          </h4>
          <p>
            You have certain rights with respect to your Personal Data. For more
            information or to submit a request, please email us at
            support@waterstress.io.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Access:</strong> Request more information about the
              Personal Data we hold about you and request a copy.
            </li>
            <li>
              <strong>Rectification:</strong> Request that we correct or
              supplement incorrect or incomplete data.
            </li>
            <li>
              <strong>Erasure:</strong> Request that we erase some or all of
              your Personal Data from our systems.
            </li>
            <li>
              <strong>Withdrawal of Consent:</strong> Withdraw your consent at
              any time if we are processing your data based on consent.
            </li>
            <li>
              <strong>Portability:</strong> Ask for a copy of your Personal Data
              in a machine-readable format.
            </li>
            <li>
              <strong>Objection:</strong> Object to the further use or
              disclosure of your Personal Data for certain purposes.
            </li>
            <li>
              <strong>Restriction of Processing:</strong> Ask us to restrict
              further processing of your Personal Data.
            </li>
            <li>
              <strong>Right to File Complaint:</strong> Lodge a complaint with
              the supervisory authority of your country or EU Member State.
            </li>
          </ul>
          <h4 className="text-base font-medium text-surface">
            Transfers of Personal Data
          </h4>
          <p>
            The Services are hosted and operated in the United States through
            WaterStress and its service providers. By using the Services, you
            acknowledge that any Personal Data about you is being provided to
            WaterStress in the U.S. and will be hosted on U.S. servers, and you
            authorize WaterStress to transfer, store, and process your
            information to and in the U.S., and possibly other countries.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Changes to this Privacy Policy
          </h2>
          <p>
            We may need to change this Privacy Policy from time to time, but we
            will alert you to any such changes by placing a notice on the
            WaterStress website, by sendinqg you an email, and/or by some other
            means. If you use the Services after any changes to the Privacy
            Policy have been posted, that means you agree to all of the changes.
          </p>
          <h2 className="text-xl font-semibold text-surface pt-4">
            Contact Information
          </h2>
          <p>
            If you have any questions or comments about this Privacy Policy,
            please contact us at:
          </p>
          <p>
            Email: support@waterstress.io
            <br />
            Address: 123 Main Street, Porterville, CA 93257
          </p>
        </div>
      </div>
    </main>
  );
}
